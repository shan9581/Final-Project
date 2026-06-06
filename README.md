# Workout Tracker

A gym progressive-overload tracker. Log your sets, get a weight/rep recommendation for your next session, and watch your estimated one-rep max trend over time.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python -m flask --app server/app.py run
```

Then open http://localhost:5000 in your browser.

## Test

```bash
pytest tests/ -v
```

## How it works

1. **Add an exercise** — give it a name and a rep range (e.g. 5–8 reps) and a weight increment (e.g. 5 lbs).
2. **Log your sets** after each session — date, weight, and reps completed.
3. **Check Next Session** — the app tells you the exact weight and rep target for your next workout using double progression:
   - If you hit the top of your rep range last session → add weight, reset reps to the bottom.
   - Otherwise → keep the weight and add one rep.
4. **Watch the trend** — each session is converted to an estimated one-rep max (Epley formula) so you can see your strength progress even as weight and reps change.
