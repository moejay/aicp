import gradio as gr

def scriptwriter_ui(project_state: gr.State):
    with gr.Blocks() as demo:
        with gr.Row():
            script_writer_to_use = gr.Dropdown(["1", "2"], label="Script Writer to use")
        with gr.Row():
            with gr.Column():
                prompt = gr.inputs.Textbox(lines=5, label="Research output")
                revert_button = gr.Button("Revert")
                save_button = gr.Button("Save")
            with gr.Column():
                rick_roll = gr.Button("Rick Roll")
                feedback = gr.Button("Feedback")

            with gr.Column():
                with gr.Tabs():
                    with gr.Tab("Feedback"):
                        feedback_text = gr.inputs.Textbox(lines=5, label="Feedback")
                    with gr.Tab("Scriptwriter"):
                        scriptwriter = gr.inputs.Textbox(lines=5, label="Scriptwriter")
        with gr.Row():
            generate_script = gr.Button("Generate script")

        with gr.Row():
            with gr.Accordion(label="Researcher Prompt to be used"):
                prompt_to_be_used = gr.outputs.Textbox(label="Prompt to be used")

        return demo

