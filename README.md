
# 3D Model Generation Tool (Shap-E Based)

This project demonstrates 3D asset generation from text prompts using OpenAI's **Shap-E** model. The output is in **.ply (Polygon File Format)**, making it compatible with 3D pipelines and game development workflows.

---


## 🎥 Video Demo

Watch a full demo of the 3D model generation process and API usage:  
[▶️ Click to watch on YouTube](https://youtu.be/ym_xpzOyj_8)

---

## Setup Instructions

### Environment Setup

```bash
cd mnt/extra

# Activate virtual environment
source shap-e-env/bin/activate


````

---

## Model Usage

### Run the API Server

```bash
cd shap-e
python server.py
```

---

## API Endpoints

| Endpoint                 | Description                     |
| ------------------------ | ------------------------------- |
| `/generate3d?prompt=...` | Generates a `.ply` 3D model     |
| `/status`                | Returns model status and uptime |

---

## Input / Output Samples

### Example Input Prompt

```
A futuristic chair with sleek design
```

### Output

* Generated `.ply` files are saved in:
  `shap_e_outputs/`

### Sample Outputs

* See `samples/ply_outputs/` for example `.ply` files:

  * `chair.ply`
  * `car.ply`



---

## Project Structure

```
mnt/extra/
├── shap-e/                   # Model code and API server
├── shap_e_outputs/           # Generated outputs (.ply)
├── samples/
│   └── ply_outputs/          # Sample .ply files (included in repo)
├── shap-e-env/               # Python virtual environment (ignored by Git)
├── README.md                 # Project documentation
├── .gitignore
```

---

## Model Details

* **Model**: Shap-E by OpenAI
* **Output Format**: `.ply` (mesh/point cloud)
* **Platform**: Local (GPU-friendly setup supported)
* **Use Case**: 3D asset generation for games and content pipelines

---

