"""NVIDIA model: deepseek-ai/deepseek-v4.1-flash  (text + image input)

    python deepseek-v4.1-flash.py "Python mein list sort kaise kare?"
    python deepseek-v4.1-flash.py "Is photo ka path aur aas-paas ka nazara 2 lines mein batao" --image path.jpg
    python deepseek-v4.1-flash.py            (chat mode)
"""

from _common import run

MODEL = "deepseek-ai/deepseek-v4.1-flash"

SETTINGS = {
    "temperature": 1,
    "top_p": 0.95,
    "max_tokens": 262144,
}

if __name__ == "__main__":
    run(MODEL, SETTINGS)
