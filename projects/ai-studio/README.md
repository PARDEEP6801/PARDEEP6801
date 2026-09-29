# AI Studio — NVIDIA ke saare models + apni khud ki LLM

Localhost web app jisme aap:
- NVIDIA (build.nvidia.com) ke **saare chat models** dropdown se use kar sakte ho
- **"Nayi LLM banao"**: base model + system prompt (personality/rules) + creativity set karke apni custom LLM save karo
- Chat streaming mein aata hai, code blocks mein **Copy** button, reasoning models (DeepSeek R1 wagera) ka "Thinking" alag dikhta hai
- OpenRouter ke free models bhi (optional key)

## 1. Zaroori software (ek baar)
| Software | Link | Note |
|---|---|---|
| Python 3.8+ | https://www.python.org/downloads/ | Windows pe install karte waqt **"Add Python to PATH"** tick karo |
| Node.js 16+ | https://nodejs.org | Sirf `npm run dev` ke liye |

Koi `pip install` / `npm install` nahi chahiye, sab built-in hai.

## 2. NVIDIA API key daalo
1. https://build.nvidia.com pe login karo, koi bhi model kholo, phir **Get API Key** dabao (`nvapi-...`)
2. Is folder ki **`.env`** file Notepad mein kholo aur key likho:
   ```
   NVIDIA_API_KEY=nvapi-xxxxxxxxxxxxxxxx
   ```
3. Save karo. **Ye key kisi ko mat bhejna** (chat mein bhi nahi).

## 3. Chalao
Is folder mein terminal kholo (Windows: folder mein address bar pe `cmd` likh ke Enter), phir:
```
npm run dev
```
Browser apne aap **http://localhost:8000** khol dega. Band karne ke liye terminal mein `Ctrl + C`.

Windows pe `start.bat` pe double-click karke bhi chala sakte ho, ya `python server.py` se.

## Apni LLM kaise banaye
1. **+ Nayi LLM banao** pe click karo
2. Naam do, e.g. "Pardeep GPT"
3. Base model chuno (Popular wale upar hain)
4. System prompt likho, e.g. *"Tum ek Hindi tutor ho. Har jawab chhota aur example ke saath do."*
5. Creativity: 0.2 = seedha/accurate, 1.0 = zyada creative
6. Save, aur baat shuru karo

Aapki LLMs `my_llms.json` mein save hoti hain. Chat history browser mein rehti hai.

## Problems?
| Problem | Fix |
|---|---|
| `NVIDIA_API_KEY is not set` | `.env` mein key daalo, save karo, server restart karo |
| `error 401/403` | Key galat ya expire ho gayi, nayi key banao |
| `error 404` on a model | Wo model NVIDIA ne hata diya, doosra chuno |
| `error 429` | Free limit / rate limit, thoda ruko ya doosra model lo |
| `Port 8000 already in use` | `.env` mein `PORT=8080` karo |
| `Python nahi mila` | Python install karo ("Add to PATH" tick karke) |
