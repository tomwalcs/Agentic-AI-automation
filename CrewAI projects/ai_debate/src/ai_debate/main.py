from dotenv import load_dotenv
import os

load_dotenv()

#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from ai_debate.crew import AiDebate

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")



def run():
    """
    Run the crew.
    """
    inputs = {
        'motion': 'There needs to be strict laws to regulate LLMs',
    }
    
    try:
        result = AiDebate().crew().kickoff(inputs=inputs)
        print(result.raw)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")

if __name__ == "__main__":
    run()
