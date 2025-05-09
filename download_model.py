from huggingface_hub import list_repo_files, hf_hub_download
import os

# Create models directory if it doesn't exist
os.makedirs("models", exist_ok=True)

# List available files in the repo
try:
    # Try TinyLlama repo
    repo_id = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
    files = list_repo_files(repo_id)
    print(f"Available files in {repo_id}:")
    gguf_files = [f for f in files if f.endswith(".gguf")]
    for file in gguf_files:
        print(f"  - {file}")
    
    if gguf_files:
        # Download the smallest q4_0 or q4_K_M model
        q4_models = [f for f in gguf_files if "q4_0" in f or "q4_K_M" in f]
        if q4_models:
            model_to_download = q4_models[0]
        else:
            model_to_download = gguf_files[0]
        
        print(f"\nDownloading {model_to_download}...")
        model_path = hf_hub_download(
            repo_id=repo_id,
            filename=model_to_download,
            local_dir="models"
        )
        print(f"Model downloaded to: {model_path}")
        print(f"File size: {os.path.getsize(model_path) / (1024 * 1024):.2f} MB")
    else:
        print("No GGUF files found in the repository.")
except Exception as e:
    print(f"Error with TinyLlama: {e}")
    
    # Try Phi-2 as an alternative
    try:
        repo_id = "TheBloke/phi-2-GGUF"
        print(f"\nTrying alternative repo: {repo_id}")
        files = list_repo_files(repo_id)
        gguf_files = [f for f in files if f.endswith(".gguf")]
        for file in gguf_files:
            print(f"  - {file}")
        
        if gguf_files:
            # Find the smallest model (likely q2_K)
            q2_models = [f for f in gguf_files if "q2_K" in f]
            if q2_models:
                model_to_download = q2_models[0]
            else:
                model_to_download = gguf_files[0]
            
            print(f"\nDownloading {model_to_download}...")
            model_path = hf_hub_download(
                repo_id=repo_id,
                filename=model_to_download,
                local_dir="models"
            )
            print(f"Model downloaded to: {model_path}")
            print(f"File size: {os.path.getsize(model_path) / (1024 * 1024):.2f} MB")
        else:
            print("No GGUF files found in the repository.")
    except Exception as e:
        print(f"Error with Phi-2: {e}")
        
        # Try one more alternative - Phi-1.5
        try:
            repo_id = "TheBloke/phi-1_5-GGUF"
            print(f"\nTrying alternative repo: {repo_id}")
            files = list_repo_files(repo_id)
            gguf_files = [f for f in files if f.endswith(".gguf")]
            for file in gguf_files:
                print(f"  - {file}")
            
            if gguf_files:
                # Find the smallest model (likely q2_K)
                q2_models = [f for f in gguf_files if "q2_K" in f]
                if q2_models:
                    model_to_download = q2_models[0]
                else:
                    model_to_download = gguf_files[0]
                
                print(f"\nDownloading {model_to_download}...")
                model_path = hf_hub_download(
                    repo_id=repo_id,
                    filename=model_to_download,
                    local_dir="models"
                )
                print(f"Model downloaded to: {model_path}")
                print(f"File size: {os.path.getsize(model_path) / (1024 * 1024):.2f} MB")
            else:
                print("No GGUF files found in the repository.")
        except Exception as e:
            print(f"Error with Phi-1.5: {e}")
            print("\nFailed to download any model. Please try downloading manually from Hugging Face.")
