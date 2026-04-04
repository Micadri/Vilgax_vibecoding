param([Parameter(ValueFromRemainingArguments=$true)] $args)
& python -m streamlit run app.py @args
