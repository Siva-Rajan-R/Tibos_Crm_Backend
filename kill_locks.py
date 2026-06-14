import asyncio
from sqlalchemy import text
from infras.primary_db.main import PG_ENGINE

async def kill_locks():
    print("Connecting to DB to check for locks...")
    async with PG_ENGINE.connect() as conn:
        # Find blocking pids
        query = text("""
        SELECT pid, state, query, wait_event_type, wait_event 
        FROM pg_stat_activity 
        WHERE state = 'idle in transaction' OR wait_event_type = 'Lock';
        """)
        res = await conn.execute(query)
        rows = res.fetchall()
        print(f"Found {len(rows)} potentially locking/idle connections.")
        for row in rows:
            print(f"PID: {row.pid}, State: {row.state}, Query: {row.query}")
            
            # Kill the connection
            if "pg_stat_activity" not in row.query:
                print(f"Terminating PID {row.pid}...")
                kill_query = text(f"SELECT pg_terminate_backend({row.pid});")
                await conn.execute(kill_query)
        
        await conn.commit()
    print("Done checking locks.")

if __name__ == "__main__":
    asyncio.run(kill_locks())
