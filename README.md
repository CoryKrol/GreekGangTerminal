# Greek Gang Terminal
Forked from my final project for the graduate level Web Programming languages class at UTDallas, Hedgehog Terminal is a stock & options tracker inspired by [ThetaGang](https://www.thetagang.com). I intend for this to be a stock tracker at first to supplement my personal spreadsheet and slowly grow into a full-featured options trading terminal

## Current Features
- Basic stock tracking and user login functionality

## Future work
- Implement position P/L tracking
- Integrate with TDAmeritrade API to auto import trades and eventually place trades
- Replace basic front-end with an Angular front-ent
- Suggest trades based on position (eg. suggest to user they can roll out positions at 21 DTE)
# How to run
1. Install dependencies with: `pip install -r requirements/dev.txt`
2. Run `set_env.sh` to set environment variables for the flask environment
3. Run `flask run` to run the application
