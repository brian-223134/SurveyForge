import os
import subprocess
from datetime import datetime
import time
import re

# Downloaded assets live outside the repo so git stays clean:
#   DATA_ROOT/database/            <- InternScience/SurveyForge_database, `database` folder
#   DATA_ROOT/Final_outline{,_First}/  <- the two zips from the same dataset
#   DATA_ROOT/gte-large-en-v1.5/   <- Alibaba-NLP/gte-large-en-v1.5
DATA_ROOT = os.environ.get(
    "SURVEYFORGE_DATA", "/data2/chanjoong/survey-agent/SurveyForge_data"
)

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")
        return True
    return False

def extract_token_usage(log_content):
    """从日志内容中提取token使用信息"""
    token_info = {
        'outline_input': 0,
        'outline_output': 0,
        'subsection_input': 0,
        'subsection_output': 0
    }
    
    patterns = {
        'outline_input': r'OutlineWriter Input token usage: (\d+)',
        'outline_output': r'OutlineWriter Output token usage: (\d+)',
        'subsection_input': r'SubsectionWriter Input token usage: (\d+)',
        'subsection_output': r'SubsectionWriter Output token usage: (\d+)'
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, log_content)
        if match:
            token_info[key] = int(match.group(1))
    
    return token_info

def run_experiment(topic, exp_num, base_path):

    save_path = os.path.join(base_path, topic, f"exp_{exp_num}")
    

    if os.path.exists(save_path):
        print(f"\nSkipping experiment {exp_num} for topic {topic} - directory already exists: {save_path}")
        return True
    

    create_directory(save_path)
    

    cmd = [
        "python", "main.py",
        "--topic", topic,
        "--gpu", "0",
        "--saving_path", save_path,
        "--model", os.environ.get("SURVEYFORGE_MODEL", "deepseek/deepseek-v4-pro"),
        "--section_num", "7",
        "--subsection_len", "500",
        "--rag_num", "100",
        "--rag_max_out", "60",
        "--outline_reference_num", "1500",
        "--survey_outline_path", DATA_ROOT,
        "--db_path", os.path.join(DATA_ROOT, "database"),
        "--embedding_model", os.path.join(DATA_ROOT, "gte-large-en-v1.5"),
        "--api_key", os.environ.get("OPENROUTER_API_KEY", ""),
        # NOTE: the "deepseek" branch of APIModel passes this to the OpenAI SDK as
        # base_url, so it must NOT include /chat/completions. The other branches do
        # expect a full endpoint path.
        "--api_url", os.environ.get("SURVEYFORGE_API_URL", "https://openrouter.ai/api/v1"),
    ]

    
    exp_start_time = datetime.now()
    
    try:
        print(f"\nRunning experiment {exp_num} for topic: {topic}")
        print(f"Saving to: {save_path}")
        print(f"Start time: {exp_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Capture the output of the process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        full_output = []
        while True:
            output = process.stdout.readline()

            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
                full_output.append(output)
        
        return_code = process.poll()
        exp_end_time = datetime.now()
        duration = exp_end_time - exp_start_time
        
        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, cmd)
        
        token_info = extract_token_usage(''.join(full_output))
        
        # Log experiment times
        log_file = os.path.join(base_path, "experiment_times.log")
        with open(log_file, "a") as f:
            f.write(f"Topic: {topic}, Exp {exp_num}\n")
            f.write(f"Start: {exp_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"End: {exp_end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duration: {duration}\n")
            f.write(f"OutlineWriter Input token usage: {token_info['outline_input']}\n")
            f.write(f"OutlineWriter Output token usage: {token_info['outline_output']}\n")
            f.write(f"SubsectionWriter Input token usage: {token_info['subsection_input']}\n")
            f.write(f"SubsectionWriter Output token usage: {token_info['subsection_output']}\n")
            f.write("-" * 50 + "\n")
        
        print(f"Experiment {exp_num} for {topic} completed successfully")
        print(f"End time: {exp_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {duration}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        exp_end_time = datetime.now()
        duration = exp_end_time - exp_start_time
        error_message = f"Error in experiment {exp_num} for {topic}: {e}"
        print(error_message)
        print(f"Failed experiment duration: {duration}")
        

        log_file = os.path.join(base_path, "experiment_times.log")
        with open(log_file, "a") as f:
            f.write(f"Topic: {topic}, Exp {exp_num} [FAILED]\n")
            f.write(f"Start: {exp_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"End: {exp_end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duration: {duration}\n")
            f.write(f"Error: {str(e)}\n")
            f.write("-" * 50 + "\n")
        
        return False

def main():

    base_path = "./output/res"
    create_directory(base_path)
    
    # Loading topics
    with open("topics_demo.txt", "r") as f:
        topics = [line.strip() for line in f if line.strip()]
    

    start_time = datetime.now()
    print(f"Starting experiments at: {start_time}")

    log_file = os.path.join(base_path, "experiment_times.log")
    log_exists = os.path.exists(log_file)
    
    with open(log_file, "a" if log_exists else "w") as f:
        if not log_exists:
            f.write(f"Experiment Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
        else:
            f.write(f"\nResuming experiments at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
    

    for topic in topics:
        print(f"\n{'='*50}")
        print(f"Starting experiments for topic: {topic}")
        print(f"{'='*50}")
        
        topic_start_time = datetime.now()
        successful_exps = 0
        
        for exp_num in range(1, 2):  
            success = run_experiment(topic, exp_num, base_path)
            if success:
                successful_exps += 1

            time.sleep(5)

        topic_end_time = datetime.now()
        topic_duration = topic_end_time - topic_start_time
        with open(log_file, "a") as f:
            f.write(f"\nTopic Summary: {topic}\n")
            f.write(f"Total Duration: {topic_duration}\n")
            f.write(f"Successful Experiments: {successful_exps}/10\n")
            f.write("=" * 50 + "\n")
        

    end_time = datetime.now()
    duration = end_time - start_time
    
    with open(log_file, "a") as f:
        f.write(f"\nFinal Summary\n")
        f.write("=" * 50 + "\n")
        f.write(f"Total Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Duration: {duration}\n")
        f.write(f"Total Topics: {len(topics)}\n")
    
    print(f"\nAll experiments completed!")
    print(f"Start time: {start_time}")
    print(f"End time: {end_time}")
    print(f"Total duration: {duration}")
    print(f"Log file saved to: {log_file}")

if __name__ == "__main__":
    main()
