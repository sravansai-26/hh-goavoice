import os
from datasets import get_dataset_config_names, load_dataset_builder

def main():
    dataset_id = "ai4bharat/MSMARCO-XI"
    print(f"Inspecting dataset: {dataset_id}")
    
    try:
        configs = get_dataset_config_names(dataset_id)
        print(f"\nAvailable configurations: {configs}")
        
        target_config = "te" # Try telugu
        if target_config not in configs:
            target_config = configs[0]
                
        print(f"\nInspecting configuration: {target_config}")
        
        builder = load_dataset_builder(dataset_id, target_config)
        
        print("\nFeatures (Schema):")
        if builder.info.features:
            for feature_name, feature_type in builder.info.features.items():
                print(f"  - {feature_name}: {feature_type}")
        else:
            print("  No features info available without loading.")
            
        print("\nSplits:")
        if builder.info.splits:
            for split_name, split_info in builder.info.splits.items():
                print(f"  - {split_name}: {split_info.num_examples} examples")
        else:
            print("  No split info available without loading.")
            
    except Exception as e:
        print(f"Error inspecting dataset: {e}")

if __name__ == "__main__":
    main()
