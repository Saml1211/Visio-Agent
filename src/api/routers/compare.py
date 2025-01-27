from fastapi import File, Form, UploadFile, HTTPException
from typing import List

@app.post("/api/compare-models")
async def compare_models(
    file: UploadFile = File(...),
    selected_models: List[str] = Form(...)
):
    try:
        content = await file.read()
        orchestrator = get_orchestrator()
        results = await orchestrator.generate_diagram(content.decode())
        
        return {
            "diagram": generate_metrics(results),
            "visualization": render_comparison_chart(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 