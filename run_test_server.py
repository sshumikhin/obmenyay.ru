import uvicorn

if __name__ == "__main__":
    uvicorn.run(app="src.main:app",
                host='localhost',
                port=7777,
                log_level="info")
