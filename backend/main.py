from fastapi import FastAPI

app = FastAPI(title="试卷图片分析和AI阅卷实验平台")

@app.get("/")
async def root():
    return {"message": "试卷图片分析和AI阅卷实验平台后端服务"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)