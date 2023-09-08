
import gradio as gr
from backend.models import AICPVideo
def research_ui(project_state: gr.State):
    with gr.Blocks() as demo:
        if project_state.value.metadata is None:
            gr.Label("Please create a project first")
            return demo
        with gr.Row():
            with gr.Column():
                gr.Label(f"Researcher to use for project: {project_state.value.metadata.title}")
                researcher_to_use = gr.Dropdown(["1", "2"], label="Researcher to use")
        with gr.Row():
            prompt = gr.inputs.Textbox(lines=5, label="Prompt")
            with gr.Column():
                rick_roll = gr.Button("Rick Roll")
                feedback = gr.Button("Feedback")

            with gr.Column():
                with gr.Tabs():
                    with gr.Tab("Feedback"):
                        feedback_text = gr.inputs.Textbox(lines=5, label="Feedback")
                    with gr.Tab("Program"):
                        program = gr.inputs.Textbox(lines=5, label="Program")
                    with gr.Tab("Researcher"):
                        researcher = gr.inputs.Textbox(lines=5, label="Researcher")
        with gr.Row():
            generate_research = gr.Button("Generate Research")

        with gr.Row():
            with gr.Accordion(label="Researcher Prompt to be used"):
                prompt_to_be_used = gr.outputs.Textbox(label="Prompt to be used")

        return demo

