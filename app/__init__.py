"""
app: the PrivyShield overlay UI.
 
Renders a transparent, always-on-top, click-through window over the real
screen and draws live blur overlays on sensitive regions detected by the
`detection` package's pipeline.
 
Run with: python -m app.overlay
"""