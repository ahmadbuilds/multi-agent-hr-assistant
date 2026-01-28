import os 
from dotenv import load_dotenv


load_dotenv('.env.local')


url=os.getenv('SUPABASE_URL')
key=os.getenv('SUPABASE_KEY')

CLERK_API_KEY=os.getenv('MOCK_API_KEY_CLERK')