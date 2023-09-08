from ui.create_project import create_project_ui
from ui.research import research_ui
from ui.scriptwriter import scriptwriter_ui
import gradio as gr
from backend.models import AICPVideo, AICPMetadata

def make_ui():
    """Prepare UI blocks"""
    with gr.Blocks() as demo:
        project_state = gr.State(AICPVideo(metadata=None, outline=None))
        with gr.Tab("Project"):
            create_project_ui(project_state)
        with gr.Tab("Research"):
            research_ui(project_state)
        with gr.Tab("Scriptwriter"):
            scriptwriter_ui(project_state)

    return demo
