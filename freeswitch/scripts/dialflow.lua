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
local API_URL = os.getenv("DIALFLOW_API_URL") or "http://api:8000"
local MAX_RETRIES = 3
local DTMF_TIMEOUT = 5000  -- 5 seconds in milliseconds

-- Response storage
local survey_responses = {}

-- Utility: HTTP GET request
function http_get(url)
    local curl = require("cURL")
    local response_body = ""
    
    local c = curl.easy{
        url = url,
        writefunction = function(str)
            response_body = response_body .. str
        end
    }
    
    local ok, err = pcall(function() c:perform() end)
    c:close()
    
    if not ok then
        freeswitch.consoleLog("err", "HTTP GET failed: " .. err .. "\n")
        return nil
    end
    
    return response_body
end

-- Utility: HTTP POST request
function http_post(url, data)
    local curl = require("cURL")
    local json = require("JSON")
    local response_body = ""
    
    local post_data = json:encode(data)
    
    local c = curl.easy{
        url = url,
        post = true,
        httpheader = {"Content-Type: application/json"},
        postfields = post_data,
        writefunction = function(str)
            response_body = response_body .. str
        end
    }
    
    local ok, err = pcall(function() c:perform() end)
    c:close()
    
    if not ok then
        freeswitch.consoleLog("err", "HTTP POST failed: " .. err .. "\n")
        return nil
    end
    
    return response_body
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
            return branch.goto
        end
    end
    -- Check for timeout branch
    for _, branch in ipairs(section.branches or {}) do
        if branch.key == "timeout" then
            return branch.goto
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
        return section.branches[1].goto
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

-- Main execution
function main(session)
    -- Answer call
    session:answer()
    
    -- Get survey ID from channel variable
    local survey_id = session:getVariable("survey_id")
    local request_uuid = session:getVariable("request_uuid")
    
    if not survey_id then
        freeswitch.consoleLog("err", "No survey_id provided\n")
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
