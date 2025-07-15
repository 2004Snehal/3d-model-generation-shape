from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
import torch
import traceback
import os
import uuid
from datetime import datetime

from shap_e.diffusion.sample import sample_latents
from shap_e.diffusion.gaussian_diffusion import diffusion_from_config
from shap_e.models.download import load_model, load_config
from shap_e.util.notebooks import decode_latent_mesh

app = FastAPI(title="Shap-E 3D Generation API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return await request_validation_exception_handler(request, exc)

xm = None
model = None
diffusion = None
device = None
model_loading_status = {"status": "not_loaded", "error": None}
model_start_time = datetime.now()

@app.on_event("startup")
async def startup_event():
    global xm, model, diffusion, device, model_loading_status
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    try:
        model_loading_status["status"] = "loading"
        xm = load_model('transmitter', device=device)
        model = load_model('text300M', device=device)
        diffusion = diffusion_from_config(load_config('diffusion'))
        model_loading_status["status"] = "loaded"
    except Exception as e:
        model_loading_status["status"] = "error"
        model_loading_status["error"] = str(e)
        traceback.print_exc()

@app.get("/status")
async def get_status():
    cuda_available = torch.cuda.is_available()
    memory_usage = None
    if cuda_available:
        try:
            memory_allocated = torch.cuda.memory_allocated(0) / 1024**3
            memory_total = torch.cuda.get_device_properties(0).total_memory / 1024**3
            memory_usage = f"{memory_allocated:.1f}GB / {memory_total:.1f}GB"
        except:
            memory_usage = "Unavailable"

    return {
        "models_loaded": all([xm, model, diffusion]),
        "model_status": model_loading_status["status"],
        "device": str(device),
        "cuda_available": cuda_available,
        "memory_usage": memory_usage,
        "error": model_loading_status.get("error"),
        "model_uptime": model_start_time.isoformat(),
        "model_version": "text300M"
    }

@app.post("/generate")
async def generate_3d_object(request: Request):
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            data = await request.json()
            prompt = data.get("prompt")
            guidance_scale = data.get("guidance_scale", 15.0)
            num_inference_steps = data.get("num_inference_steps", 64)
            seed = data.get("seed")
        else:
            form_data = await request.form()
            prompt = form_data.get("prompt")
            guidance_scale = float(form_data.get("guidance_scale", 15.0))
            num_inference_steps = int(form_data.get("num_inference_steps", 64))
            seed_val = form_data.get("seed")
            seed = int(seed_val) if seed_val and seed_val.strip() else None

        if not prompt:
            raise HTTPException(status_code=422, detail="Prompt is required")
        if not all([xm, model, diffusion]):
            raise HTTPException(status_code=503, detail="Models not loaded")

        if seed is not None:
            torch.manual_seed(seed)

        latents = sample_latents(
            batch_size=1,
            model=model,
            diffusion=diffusion,
            guidance_scale=guidance_scale,
            model_kwargs=dict(texts=[prompt]),
            progress=True,
            clip_denoised=True,
            use_fp16=True,
            use_karras=True,
            karras_steps=num_inference_steps,
            sigma_min=1e-3,
            sigma_max=160,
            s_churn=0,
        )

        mesh = decode_latent_mesh(xm, latents[0]).tri_mesh()

        output_dir = "/mnt/extra/shap_e_outputs"
        os.makedirs(output_dir, exist_ok=True)
        output_id = str(uuid.uuid4())
        output_path = os.path.join(output_dir, f"shap_e_output_{output_id}.obj")

        with open(output_path, 'wb') as f:
            mesh.write_obj(f)

        return {
            "message": "3D object generated successfully",
            "prompt": prompt,
            "output_id": output_id,
            "download_url": f"/download/{output_id}.obj",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = f"/mnt/extra/shap_e_outputs/shap_e_output_{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=filename
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)