import os

dirs = ['src/api', 'src/api/routers', 'tests/api']
for d in dirs:
    os.makedirs(d, exist_ok=True)

routers = ['companies', 'screener', 'sectors', 'peers', 'valuation', 'portfolio', 'documents']
for r in routers:
    with open(f'src/api/routers/{r}.py', 'w') as f:
        f.write(f'''from fastapi import APIRouter

router = APIRouter()

@router.get("/{r}")
def get_{r}():
    return {{"message": "{r} route"}}
''')

# empty __init__.py files
open('src/api/__init__.py', 'w').close()
open('src/api/routers/__init__.py', 'w').close()
open('tests/api/__init__.py', 'w').close()

print("Scaffold complete.")
