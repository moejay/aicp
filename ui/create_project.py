import gradio as gr
from backend.models import AICPMetadata

def create_new_project(title, selected_program, project_state):
    project_state.metadata = AICPMetadata(
            title=title,
            description=None,
            program=selected_program,
            original_prompt=None,
            research_result=None
            )
    return project_state

def create_project_ui(project_state: gr.State):
    with gr.Blocks() as demo:
        with gr.Row():
            selected_program = gr.Dropdown (["1", "2"], label="Program")
            title = gr.inputs.Textbox(lines=1, label="Title")
        with gr.Row():
            create_new_project_btn = gr.Button("Create new project")
            create_new_project_btn.click(create_new_project, [title, selected_program, project_state], [project_state])
    return demo
