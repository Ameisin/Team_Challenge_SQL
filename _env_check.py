import os
from dotenv import dotenv_values

base = r"C:\Users\ak471\Documents\Github\Team_Challenge_SQL"
d = dotenv_values(os.path.join(base, ".env"))
for k, v in d.items():
    state = "SET" if v else "EMPTY"
    n = len(v) if v else 0
    print(k, "=", state, "(", n, "chars )")
creds = os.path.join(base, "credentials", "service-account.json")
print("credentials file exists:", os.path.exists(creds))
