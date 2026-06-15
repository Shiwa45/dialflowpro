--[[
DialFlow Pro - FreeSWITCH Lua Script
IVR execution engine for survey/campaign calls.

This script:
1. Fetches survey data from Django API
2. Executes IVR flow (10 section types)
3. Handles DTMF input and branching
4. Posts responses back to Django

Called from FreeSWITCH with channel variables:
- survey_id: Survey to execute
- request_uuid: Callrequest UUID
- api_url: Django API base URL (http://api:8000)
]]

-- Configuration
-- Windows host IP as seen from WSL2 (set DIALFLOW_API_URL env var to override)
local API_URL = os.getenv("DIALFLOW_API_URL") or "http://172.31.48.1:8000"
local FS_INTERNAL_PROFILE = os.getenv("FS_INTERNAL_PROFILE") or "internal"
local MAX_RETRIES = 3
local DTMF_TIMEOUT = 5000  -- 5 seconds in milliseconds

-- Response storage
local survey_responses = {}

-- ── Debug file logger ─────────────────────────────────────────────────────────
-- Writes a trace to /tmp/dialflow.log (read with: wsl -d Debian -- cat /tmp/dialflow.log)
-- so we can see exactly what the script does on each call, beyond the FS console.
local LOG_FILE = os.getenv("DIALFLOW_LOG") or "/tmp/dialflow.log"
function dlog(msg)
    freeswitch.consoleLog("INFO", "[dialflow] " .. tostring(msg) .. "\n")
    local f = io.open(LOG_FILE, "a")
    if f then
        f:write(os.date("%Y-%m-%d %H:%M:%S") .. "  " .. tostring(msg) .. "\n")
        f:close()
    end
end

-- ── HTTP via the system `curl` binary (no external Lua modules needed) ────────
-- The lua-cURL binding is NOT installed in this FreeSWITCH build, so we shell
-- out to /usr/bin/curl via io.popen. Full control over headers (incl X-Tenant)
-- and no dependency on the `cURL`/`JSON` Lua modules.

-- Single-quote a string safely for the shell.
local function shq(s)
    return "'" .. tostring(s):gsub("'", "'\\''") .. "'"
end

-- Minimal JSON encoder for a FLAT table (string/number/boolean values).
-- nil values are naturally absent (Lua tables can't hold nil), so optional
-- fields are simply omitted — the Django webhooks default them.
local function json_encode_flat(t)
    local parts = {}
    for k, v in pairs(t) do
        local tv, val = type(v), nil
        if tv == "number" or tv == "boolean" then
            val = tostring(v)
        elseif tv == "string" then
            val = '"' .. v:gsub('\\', '\\\\'):gsub('"', '\\"') .. '"'
        else
            val = "null"
        end
        parts[#parts + 1] = '"' .. tostring(k) .. '":' .. val
    end
    return "{" .. table.concat(parts, ",") .. "}"
end

-- Utility: HTTP GET request
function http_get(url)
    local cmd = "curl -s -m 15 " .. shq(url) .. " 2>/dev/null"
    local p = io.popen(cmd)
    if not p then dlog("io.popen failed (GET)"); return nil end
    local body = p:read("*a")
    p:close()
    return body
end

-- Utility: HTTP POST request (JSON body)
-- extra_headers: optional list of header strings (e.g. {"X-Tenant: test_tenant"})
function http_post(url, data, extra_headers)
    local body = json_encode_flat(data)

    local cmd = "curl -s -m 15 -X POST " .. shq(url)
             .. " -H " .. shq("Content-Type: application/json")
    if extra_headers then
        for _, h in ipairs(extra_headers) do
            cmd = cmd .. " -H " .. shq(h)
        end
    end
    cmd = cmd .. " --data " .. shq(body) .. " 2>/dev/null"

    dlog("HTTP POST -> " .. url .. " body=" .. body)
    local p = io.popen(cmd)
    if not p then
        dlog("io.popen failed (POST)")
        return nil
    end
    local resp = p:read("*a")
    p:close()
    dlog("HTTP POST response: " .. tostring(resp))
    return resp
end

-- Fetch survey data from Django
function get_survey_data(survey_id)
    local url = API_URL .. "/api/survey/surveys/" .. survey_id .. "/get_survey_data/"
    freeswitch.consoleLog("info", "Fetching survey: " .. url .. "\n")
    
    local response = http_get(url)
    if not response then
        return nil
    end
    
    local json = require("JSON")
    return json:decode(response)
end

-- Find section by ID
function find_section(survey, section_id)
    for _, section in ipairs(survey.sections) do
        if section.id == section_id then
            return section
        end
    end
    return nil
end

-- Find branch for given key
function find_branch(section, key)
    for _, branch in ipairs(section.branches or {}) do
        if branch.key == key or branch.key == "any" then
            return branch["goto"]
        end
    end
    -- Check for timeout branch
    for _, branch in ipairs(section.branches or {}) do
        if branch.key == "timeout" then
            return branch["goto"]
        end
    end
    return nil
end

-- Play audio file
function play_audio(session, audio_url)
    if not audio_url then
        freeswitch.consoleLog("warning", "No audio URL provided\n")
        return false
    end
    
    freeswitch.consoleLog("info", "Playing audio: " .. audio_url .. "\n")
    session:streamFile(audio_url)
    return true
end

-- Read DTMF digits
function read_dtmf(session, min_digits, max_digits, timeout_ms)
    timeout_ms = timeout_ms or DTMF_TIMEOUT
    local digits = session:read(min_digits, max_digits, "", timeout_ms, "#")
    return digits
end

-- Section Type 1: PLAY_MESSAGE
function execute_play_message(session, section)
    freeswitch.consoleLog("info", "Executing PLAY_MESSAGE: " .. section.name .. "\n")
    play_audio(session, section.audio_url)
    
    survey_responses[section.id] = {
        type = "play_message",
        played = true
    }
    
    -- Auto-advance to first branch or nil
    if section.branches and #section.branches > 0 then
        return section.branches[1]["goto"]
    end
    return nil
end

-- Section Type 2: MULTI_CHOICE
function execute_multi_choice(session, section)
    freeswitch.consoleLog("info", "Executing MULTI_CHOICE: " .. section.name .. "\n")
    
    local retries = 0
    local max_retries = section.retries or MAX_RETRIES
    
    while retries <= max_retries do
        play_audio(session, section.audio_url)
        
        local digit = read_dtmf(session, 1, 1)
        
        if digit and digit ~= "" then
            -- Valid digit received
            local next_section = find_branch(section, digit)
            
            if next_section then
                survey_responses[section.id] = {
                    type = "multi_choice",
                    key_pressed = digit,
                    key_label = section.keys[digit]
                }
                return next_section
            end
        end
        
        -- Invalid input
        retries = retries + 1
        if retries <= max_retries and section.invalid_audio_url then
            play_audio(session, section.invalid_audio_url)
        end
    end
    
    -- Max retries exceeded - timeout branch
    return find_branch(section, "timeout")
end

-- Section Type 3: RATING_QUESTION
function execute_rating_question(session, section)
    freeswitch.consoleLog("info", "Executing RATING_QUESTION: " .. section.name .. "\n")
    
    play_audio(session, section.audio_url)
    
    local min = section.min_digits or 1
    local max = section.max_digits or 2
    local digits = read_dtmf(session, min, max)
    
    if digits and digits ~= "" then
        local rating = tonumber(digits)
        survey_responses[section.id] = {
            type = "rating",
            rating = rating
        }
        
        -- Find branch or continue
        return find_branch(section, "any")
    end
    
    return find_branch(section, "timeout")
end

-- Section Type 4: CAPTURE_DIGITS
function execute_capture_digits(session, section)
    freeswitch.consoleLog("info", "Executing CAPTURE_DIGITS: " .. section.name .. "\n")
    
    play_audio(session, section.audio_url)
    
    local min = section.min_digits or 1
    local max = section.max_digits or 10
    local timeout = (section.timeout or 5) * 1000
    
    local digits = read_dtmf(session, min, max, timeout)
    
    if digits and digits ~= "" then
        survey_responses[section.id] = {
            type = "capture_digits",
            digits = digits
        }
        return find_branch(section, "any")
    end
    
    return find_branch(section, "timeout")
end

-- Section Type 5: RECORD_MESSAGE
function execute_record_message(session, section)
    freeswitch.consoleLog("info", "Executing RECORD_MESSAGE: " .. section.name .. "\n")
    
    play_audio(session, section.audio_url)
    
    local max_time = section.max_time or 30
    local filename = "/tmp/recording_" .. session:get_uuid() .. ".wav"
    
    session:recordFile(filename, max_time, 200, 3)
    
    survey_responses[section.id] = {
        type = "record_message",
        filename = filename,
        recorded = true
    }
    
    return find_branch(section, "any")
end

-- Section Type 6: CALL_TRANSFER
function execute_call_transfer(session, section)
    freeswitch.consoleLog("info", "Executing CALL_TRANSFER: " .. section.name .. "\n")
    
    if section.number then
        session:transfer(section.number, "XML", "default")
        survey_responses[section.id] = {
            type = "call_transfer",
            number = section.number,
            transferred = true
        }
    end
    
    return nil  -- End survey after transfer
end

-- Section Type 7: HANGUP
function execute_hangup(session, section)
    freeswitch.consoleLog("info", "Executing HANGUP: " .. section.name .. "\n")
    
    if section.audio_url then
        play_audio(session, section.audio_url)
    end
    
    survey_responses[section.id] = {
        type = "hangup"
    }
    
    session:hangup()
    return nil
end

-- Section Type 8: CONFERENCE
function execute_conference(session, section)
    freeswitch.consoleLog("info", "Executing CONFERENCE: " .. section.name .. "\n")
    
    if section.conference_number then
        session:execute("conference", section.conference_number)
    end
    
    return nil  -- End survey after conference
end

-- Section Type 9: DNC
function execute_dnc(session, section)
    freeswitch.consoleLog("info", "Executing DNC: " .. section.name .. "\n")
    
    local phone = session:getVariable("destination_number")
    
    -- TODO: Add to DNC list via API
    -- http_post(API_URL .. "/api/dnc/add/", {phone_number = phone})
    
    survey_responses[section.id] = {
        type = "dnc",
        phone_number = phone,
        added_to_dnc = true
    }
    
    if section.audio_url then
        play_audio(session, section.audio_url)
    end
    
    return find_branch(section, "any")
end

-- Section Type 10: SMS
function execute_sms(session, section)
    freeswitch.consoleLog("info", "Executing SMS: " .. section.name .. "\n")
    
    -- TODO: Send SMS via API
    -- local phone = session:getVariable("destination_number")
    -- http_post(API_URL .. "/api/sms/send/", {
    --     to = phone,
    --     message = section.sms_text
    -- })
    
    survey_responses[section.id] = {
        type = "sms",
        sent = true
    }
    
    return find_branch(section, "any")
end

-- Execute section based on type
function execute_section(session, section)
    local section_type = section.type
    
    if section_type == 1 then
        return execute_play_message(session, section)
    elseif section_type == 2 then
        return execute_multi_choice(session, section)
    elseif section_type == 3 then
        return execute_rating_question(session, section)
    elseif section_type == 4 then
        return execute_capture_digits(session, section)
    elseif section_type == 5 then
        return execute_record_message(session, section)
    elseif section_type == 6 then
        return execute_call_transfer(session, section)
    elseif section_type == 7 then
        return execute_hangup(session, section)
    elseif section_type == 8 then
        return execute_conference(session, section)
    elseif section_type == 9 then
        return execute_dnc(session, section)
    elseif section_type == 10 then
        return execute_sms(session, section)
    end
    
    return nil
end

-- Post survey responses to Django
function post_survey_response(survey_id, callrequest_id, responses)
    local url = API_URL .. "/api/survey/responses/"
    local data = {
        survey = survey_id,
        callrequest = callrequest_id,
        response_data = responses,
        completed = true
    }
    
    freeswitch.consoleLog("info", "Posting survey responses\n")
    local response = http_post(url, data)
    
    return response ~= nil
end

-- Report call completion back to Django (frees subscriber + pacing capacity)
function post_hangup(session, answered_epoch, disposition)
    local request_uuid = session:getVariable("request_uuid") or ""
    if request_uuid == "" then return end

    local billsec = 0
    if answered_epoch then billsec = os.time() - answered_epoch end

    local hangup_cause = session:hangupCause() or "NORMAL_CLEARING"
    local tenant_schema = session:getVariable("tenant_schema") or ""
    local agent_id = session:getVariable("dialflow_agent_id")

    local payload = {
        callid        = session:get_uuid(),
        request_uuid  = request_uuid,
        tenant_schema = tenant_schema,
        agent_id      = agent_id and tonumber(agent_id) or nil,
        callerid      = session:getVariable("caller_id_number") or "",
        duration      = billsec,
        billsec       = billsec,
        disposition   = disposition or "ANSWER",
        hangup_cause  = hangup_cause,
    }
    http_post(
        API_URL .. "/api/dialer-cdr/webhook/hangup/",
        payload,
        {"X-Tenant: " .. tenant_schema}
    )
end


-- Route answered predictive/progressive call to an available agent
function route_to_agent(session)
    local call_id      = session:get_uuid()
    local campaign_id  = session:getVariable("campaign_id") or ""
    local caller_number = session:getVariable("caller_id_number")
                       or session:getVariable("destination_number")
                       or ""
    local tenant_id    = session:getVariable("tenant_id") or ""
    local tenant_schema = session:getVariable("tenant_schema") or ""

    dlog("route_to_agent: call_id=" .. call_id .. " campaign=" .. campaign_id ..
         " tenant_schema=" .. tenant_schema .. " caller=" .. caller_number)

    local payload = {
        call_id       = call_id,
        caller_number = caller_number,
        campaign_id   = campaign_id ~= "" and tonumber(campaign_id) or nil,
        tenant_id     = tenant_id ~= "" and tonumber(tenant_id) or nil,
        tenant_schema = tenant_schema,
    }

    local response = http_post(
        API_URL .. "/api/callcenter/route-call/",
        payload,
        {"X-Tenant: " .. tenant_schema}
    )
    if not response then
        dlog("route-call API unreachable — hanging up")
        return false
    end

    -- Parse the simple flat JSON response with string matching (no JSON module
    -- dependency). Response shape:
    --   {"available":true,"agent_id":3,"agent_name":"...","agent_extension":"1001"}
    local available = response:match('"available"%s*:%s*true') ~= nil
    local ext       = response:match('"agent_extension"%s*:%s*"([^"]*)"')
    local agent_id  = response:match('"agent_id"%s*:%s*(%d+)')

    if not available or not ext or ext == "" then
        dlog("No agent available (response=" .. tostring(response) .. ") — hanging up")
        return false
    end

    dlog("Agent found: ext=" .. ext .. " agent_id=" .. tostring(agent_id))

    -- Remember which agent took the call so post_hangup can recycle them
    -- (returns the agent to Waiting) without depending on fs_event_listener.
    if agent_id then
        session:setVariable("dialflow_agent_id", agent_id)
    end

    -- Resolve the agent's ACTUAL registered SIP contact. Plain
    -- "sofia/internal/1001" fails with USER_NOT_REGISTERED because the
    -- profile's default domain doesn't match the phone's registration realm.
    -- sofia_contact returns the exact contact URI the phone registered with.
    local api = freeswitch.API()
    local contact = api:executeString("sofia_contact " .. FS_INTERNAL_PROFILE .. "/" .. ext)
    contact = (contact or ""):gsub("%s+$", "")
    local dialstr
    if contact ~= "" and not contact:find("error") and not contact:find("user_not_registered") then
        dialstr = contact                       -- e.g. sofia/internal/sip:1001@ip:port;...
    else
        dialstr = "user/" .. ext                -- fallback: directory lookup
    end

    -- Tell the agent desktop the call is now active (panel auto-shows the
    -- in-call screen — no manual 'Answer' click needed).
    if agent_id then
        http_post(
            API_URL .. "/api/callcenter/call-answered/",
            { agent_id = tonumber(agent_id), call_id = call_id },
            {"X-Tenant: " .. tenant_schema}
        )
    end

    -- Bridge the customer leg to the agent's phone via the `bridge` app.
    -- (session:bridge() expects a Session object, so we use execute().)
    local answered_epoch = os.time()
    dlog("executing bridge -> " .. dialstr .. " (sofia_contact=" .. tostring(contact) .. ")")
    session:execute("bridge", dialstr)
    dlog("bridge returned (call ended). hangup_cause=" .. tostring(session:hangupCause()))

    -- Bridge ended → report hangup so the call completes & frees capacity
    post_hangup(session, answered_epoch, "ANSWER")
    return true
end


-- Route an answered call to an AI voice agent via LiveKit SIP.
-- The customer leg is bridged to the LiveKit gateway; X-* SIP headers carry
-- the AIAgent id + tenant so LiveKit dispatches the right agent (see the SIP
-- trunk's headers_to_attributes mapping in livekit_sip_setup.py).
function route_to_ai(session)
    local ai_agent_id   = session:getVariable("ai_agent_id") or ""
    local tenant_schema = session:getVariable("tenant_schema") or ""
    local caller        = session:getVariable("caller_id_number") or ""
    dlog("route_to_ai: ai_agent_id=" .. ai_agent_id .. " tenant=" .. tenant_schema ..
         " caller=" .. caller)

    if ai_agent_id == "" then
        dlog("route_to_ai: no ai_agent_id — cannot route")
        return false
    end

    local gw = os.getenv("LIVEKIT_SIP_GATEWAY") or "livekit"

    -- B-LEG variables must be set inside the dial-string braces — variables
    -- `set` on the A-leg do NOT appear on the outbound INVITE to LiveKit.
    --   sip_h_X-*          routing info (trunk maps them to attributes)
    --   rtp_secure_media   LiveKit Cloud requires SRTP media
    --   absolute_codec_string  8kHz telephony codec for the worker pipeline
    -- NOTE: no rtp_secure_media here — LiveKit Cloud answers plain RTP and the
    -- forced-SRTP offer fails negotiation (INCOMPATIBLE_DESTINATION). TLS
    -- secures signaling; media runs plain RTP, which LiveKit accepts.
    local blegvars = table.concat({
        "sip_h_X-Agent-Id=" .. ai_agent_id,
        "sip_h_X-Tenant-Schema=" .. tenant_schema,
        "sip_h_X-Caller-Number=" .. caller,
        "absolute_codec_string=PCMU",
    }, ",")
    -- Dial the FIXED trunk number (must match the LiveKit inbound trunk's
    -- `numbers`). Which AI agent handles the call rides in X-Agent-Id.
    local lk_number = os.getenv("LIVEKIT_TRUNK_NUMBER") or "+918000000001"
    local dialstr = "{" .. blegvars .. "}sofia/gateway/" .. gw .. "/" .. lk_number

    local answered_epoch = os.time()
    dlog("bridging to LiveKit AI -> " .. dialstr)
    session:execute("bridge", dialstr)

    -- Did the B-leg actually connect? bridge leaves the result on the A-leg.
    local disp   = session:getVariable("originate_disposition") or ""
    local bcause = session:getVariable("bridge_hangup_cause") or ""
    dlog("AI bridge result: originate_disposition=" .. disp ..
         " bridge_hangup_cause=" .. bcause)

    local ok = (disp == "SUCCESS") or (bcause == "NORMAL_CLEARING")
    post_hangup(session, answered_epoch, ok and "ANSWER" or "FAILED")
    return ok
end


-- Main execution
function main(session)
    local dial_mode = tonumber(session:getVariable("dial_mode") or "0")
    dlog("=== main() entered: dial_mode=" .. tostring(dial_mode) ..
         " uuid=" .. tostring(session:get_uuid()) ..
         " answered=" .. tostring(session:answered()))

    -- Answer call
    session:answer()
    dlog("session answered, ready=" .. tostring(session:ready()))

    -- ── Predictive / Progressive mode: route to AI or human, skip IVR ──
    if dial_mode == 1 or dial_mode == 3 then
        local ai_agent_id = session:getVariable("ai_agent_id") or ""
        local ok
        if ai_agent_id ~= "" then
            ok = route_to_ai(session)          -- AI campaign → LiveKit
            dlog("route_to_ai returned ok=" .. tostring(ok))
        else
            ok = route_to_agent(session)       -- human campaign → softphone
            dlog("route_to_agent returned ok=" .. tostring(ok))
        end
        if not ok then
            session:hangup("NO_USER_RESPONSE")
        end
        return
    end

    -- ── IVR / Survey mode ─────────────────────────────────────
    local survey_id = session:getVariable("survey_id")
    local request_uuid = session:getVariable("request_uuid")

    if not survey_id then
        freeswitch.consoleLog("err", "No survey_id and not predictive mode\n")
        session:hangup()
        return
    end
    
    freeswitch.consoleLog("info", "Starting survey: " .. survey_id .. "\n")
    
    -- Fetch survey data
    local survey = get_survey_data(survey_id)
    if not survey then
        freeswitch.consoleLog("err", "Failed to fetch survey data\n")
        session:hangup()
        return
    end
    
    -- Start at entry section
    local current_section_id = survey.entry_section
    local iterations = 0
    local max_iterations = 100  -- Prevent infinite loops
    
    -- Execute survey flow
    while current_section_id and iterations < max_iterations do
        local section = find_section(survey, current_section_id)
        
        if not section then
            freeswitch.consoleLog("err", "Section not found: " .. current_section_id .. "\n")
            break
        end
        
        -- Execute section
        local next_section_id = execute_section(session, section)
        current_section_id = next_section_id
        iterations = iterations + 1
    end
    
    -- Post responses
    if request_uuid then
        post_survey_response(survey_id, request_uuid, survey_responses)
    end
    
    freeswitch.consoleLog("info", "Survey completed\n")
end

-- Entry point
if session then
    main(session)
else
    freeswitch.consoleLog("err", "No session available\n")
end
