import django, os, time
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.development'
django.setup()
from apps.dialer_cdr.esl import get_esl_connection
c = get_esl_connection("fs1")
print("reloadxml:", (getattr(c.send("api reloadxml"),"data","") or "").strip()[:60])
print("restart external:", (getattr(c.send("api sofia profile external restart"),"data","") or "").strip()[:80])
time.sleep(6)
# Is TLS bound on external?
st = (getattr(c.send("api sofia status"),"data","") or "")
for line in st.splitlines():
    if "external" in line.lower():
        print("  ", line.strip())
