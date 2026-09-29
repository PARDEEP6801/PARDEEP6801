# Models: har model ki alag file

Is folder mein har NVIDIA model ki apni file hai, jiska naam model ke naam par hai.
Sab files ek hi API key use karti hain, jo `ai-studio/.env` mein `NVIDIA_API_KEY` ke naam se rakhi hai.

| File | Model | Kya kar sakta hai |
|---|---|---|
| `deepseek-v4.1-flash.py` | `deepseek-ai/deepseek-v4.1-flash` | Text + image |

## Ek baar setup
```
pip install -r ../requirements.txt
```

## Chalana
Is folder (`models`) mein terminal kholo:
```
python deepseek-v4.1-flash.py "Mera sawal"
python deepseek-v4.1-flash.py "Is photo mein kya hai?" --image C:\Users\Pardeep\Desktop\photo.jpg
python deepseek-v4.1-flash.py
```
Sirf `python deepseek-v4.1-flash.py` chalane se chat mode khulta hai. Chat mode mein image bhejni ho toh aise likho: `image photo.jpg is photo mein kya hai?`

## Naya model jodna
NVIDIA site (build.nvidia.com) pe model ka Python code copy karke bhejo, main uski file bana dunga.
