import safetensors.torch as st
try:
    st.safe_open('/tmp/empty.safetensors', framework='pt', device='cpu')
except Exception as e:
    print(repr(e))
