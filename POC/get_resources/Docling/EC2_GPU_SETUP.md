# AWS EC2 GPU Setup for Docling

## Instance Recommendation

| Field | Value |
|---|---|
| **Instance type** | `g4dn.xlarge` — 4 vCPU, 16 GB RAM, NVIDIA T4 (16 GB VRAM) |
| **Spot price** | ~$0.16/hr (vs $0.53/hr on-demand) |
| **AMI** | *AWS Deep Learning Base OSS Nvidia Driver GPU AMI (Ubuntu 22.04)* |
| **Storage** | 50 GB gp3 (models + output) |
| **Region** | Any — `eu-central-1` or `us-east-1` recommended for availability |

> Use a Spot Instance for cost savings — Docling conversion is interruptible and fast enough to restart.

---

## 1. Launch the Instance

```bash
# Via AWS CLI (adjust --key-name and --security-group-ids)
aws ec2 run-instances \
  --image-id ami-xxxxxxxxxxxxxxxxx \       # find Deep Learning AMI ID for your region
  --instance-type g4dn.xlarge \
  --key-name your-key-pair \
  --security-group-ids sg-xxxxxxxxx \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":50,"VolumeType":"gp3"}}]' \
  --instance-market-options '{"MarketType":"spot"}' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=docling-poc}]'
```

**Find the correct AMI ID for your region:**
```bash
aws ec2 describe-images \
  --owners amazon \
  --filters "Name=name,Values=*Deep Learning Base OSS Nvidia Driver GPU AMI*Ubuntu*22.04*" \
  --query "sort_by(Images, &CreationDate)[-1].ImageId" \
  --output text
```

---

## 2. Connect

```bash
ssh -i your-key-pair.pem ubuntu@<ec2-public-ip>
```

---

## 3. Verify GPU

```bash
nvidia-smi
```

Expected: T4 GPU listed with driver version ≥ 535.

---

## 4. Transfer Project Files

From your local machine:
```bash
PDF="XS2A-API-as-PSD2-Interface-Implementation-Guidelines-2.4.pdf"

scp -i your-key-pair.pem \
  convert.py postprocess.py split_sections.py validate.py .env "$PDF" \
  ubuntu@<ec2-public-ip>:~/docling-poc/
```

---

## 5. Set Up Environment on EC2

```bash
cd ~/docling-poc

# Create venv
python3 -m venv .venv
source .venv/bin/activate

# Install CUDA-enabled PyTorch (replaces the CPU-only build)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install Docling and dependencies
pip install docling docling-core langchain-text-splitters tiktoken python-dotenv accelerate

# Verify GPU is visible to PyTorch
python3 -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('Device:', torch.cuda.get_device_name(0))"
```

Expected output:
```
CUDA available: True
Device: Tesla T4
```

---

## 6. Run the Pipeline

```bash
PDF="XS2A-API-as-PSD2-Interface-Implementation-Guidelines-2.4.pdf"
source .venv/bin/activate

python convert.py "$PDF"
python postprocess.py "$PDF"
python split_sections.py "$PDF"
python validate.py "$PDF"
```

---

## 7. Copy Results Back

```bash
# From local machine
scp -i your-key-pair.pem -r \
  ubuntu@<ec2-public-ip>:~/docling-poc/output \
  ./output-from-ec2
```

---

## 8. Stop the Instance

```bash
aws ec2 stop-instances --instance-ids <instance-id>
```

> **Important:** Stop (not terminate) to preserve the EBS volume if you need to re-run. Terminate when done to avoid storage charges.

---

## Cost Estimate

| Item | Rate | Est. for one 100-page PDF |
|---|---|---|
| g4dn.xlarge Spot | ~$0.16/hr | ~$0.05–$0.10 (20–40 min) |
| EBS gp3 50 GB | ~$0.08/GB/month | ~$0.001 per run |
| Data transfer out | $0.09/GB | negligible |
| **Total** | | **< $0.15 per run** |
