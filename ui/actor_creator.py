# A Gradio demo that helps to create a new actor
# We need to give the actor the following:
# 1. Name
# 2. Bio
# 3. A Speaker voice
# 4. A base image (or lora)
import os
import gradio as gr
import openai
import yaml
from shutil import copy2
from utils import utils
from utils.voice_gen import generate_audio_from_sentence


TEST_PREFIX = "tmp/actor_creator"


def generate_bio(actor_name, actor_bio):
    """Generate a bio for the actor"""
    openai.api_key = os.environ["OPENAI_API_KEY"]
    retries = 3
    while retries > 0:
        try:
            msg = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a bio writer for an actor.
                            Write a brief bio describing the actor, be concise
                            and make sure to describe the actor's demeanor and personality in the bio.
                            Also create an appropriate physical description of the actor, describing
                            the gender, skin color, hair color, body type, possible clothes and any other relevant physical attributes, in comma separated format.
                            Also create a catch phrase this actor would say, you can be creative here and you are allowedd to swear
                            
                            Always return the result as YAML with the following format:
                            name: <name>
                            bio: <bio>
                            physical: <physical description>
                            catch_phrase: <catch phrase>
                            """,
                    },
                    {
                        "role": "user",
                        "content": f"""
                        Actor Name: {actor_name}
                        Actor Bio: {actor_bio}
                            """,
                    },
                ],
            )
            print(msg)
            response = msg.choices[0].message.content
            response = yaml.load(response, Loader=yaml.FullLoader)
            assert response.get("name") is not None
            assert response.get("bio") is not None
            assert response.get("physical") is not None
            assert response.get("catch_phrase") is not None
            return response["bio"], response["physical"], response["catch_phrase"]
        except Exception as e:
            retries -= 1
            print(e)
            continue
    return "Error", "Error"


def step_1_generate_voices(sentence, num_samples_to_generate, text_temp, waveform_temp):
    """Generate 20 voices for the actor"""
    os.makedirs(TEST_PREFIX, exist_ok=True)
    voices = []
    for i in range(num_samples_to_generate):
        output_file = os.path.join(TEST_PREFIX, f"testvoice-{i}.wav")
        voice, _ = generate_audio_from_sentence(
            sentence,
            speaker=None,
            output_file=output_file,
            output_full=True,
            text_temp=text_temp,
            waveform_temp=waveform_temp,
        )
        voices.append(voice)

    return gr.Dropdown.update(choices=voices)


def step_2_generate_voice_variations(sentence, voice, text_temp, waveform_temp):
    """Generate variations of the voice"""
    variations = []

    num_to_generate = 3
    start_gen = 0.02
    # Generate 10 variations on text_temp where the median is text_temp and the range is 0.1 on either side
    # Keeping waveform_temp constant
    for i in range(num_to_generate):
        new_text_temp = text_temp - start_gen + (i * 0.02)
        new_waveform_temp = waveform_temp
        output_file = voice.replace(".wav", f"-{new_text_temp}-{new_waveform_temp}.wav")
        new_file, _ = generate_audio_from_sentence(
            sentence,
            speaker=voice.replace(".wav", ".npz"),
            output_file=output_file,
            output_full=False,
            text_temp=new_text_temp,
            waveform_temp=new_waveform_temp,
        )
        variations.append(new_file)

    # Generate 10 variations on waveform_temp where the median is waveform_temp and the range is 0.1 on either side
    # Keeping text_temp constant
    for i in range(num_to_generate):
        new_waveform_temp = waveform_temp - start_gen + (i * 0.02)
        new_text_temp = text_temp
        output_file = voice.replace(".wav", f"-{new_text_temp}-{new_waveform_temp}.wav")
        new_file, _ = generate_audio_from_sentence(
            sentence,
            speaker=voice.replace(".wav", ".npz"),
            output_file=output_file,
            output_full=False,
            text_temp=new_text_temp,
            waveform_temp=new_waveform_temp,
        )
        variations.append(new_file)

    # Generate 10 variations on both text_temp and waveform_temp where the median is text_temp and waveform_temp and the range is 0.1 on either side
    for i in range(num_to_generate):
        new_waveform_temp = waveform_temp - start_gen + (i * 0.02)
        new_text_temp = text_temp - start_gen + (i * 0.02)
        output_file = voice.replace(".wav", f"-{new_text_temp}-{new_waveform_temp}.wav")
        new_file, _ = generate_audio_from_sentence(
            sentence,
            speaker=voice.replace(".wav", ".npz"),
            output_file=output_file,
            output_full=False,
            text_temp=new_text_temp,
            waveform_temp=new_waveform_temp,
        )
        variations.append(new_file)

    return gr.Dropdown.update(choices=variations)


def step_3_generate_test_from_voice_variation(sentence, voice, voice_variation):
    """Generate a test from the voice variation"""
    output_file = f"vo-variation-test.wav"
    # extract text_temp and waveform_temp from the filename
    text_temp, waveform_temp = voice_variation.replace(".wav", "").split("-")[-2:]
    text_temp = float(text_temp)
    waveform_temp = float(waveform_temp)
    new_audio, _ = generate_audio_from_sentence(
        sentence,
        speaker=voice.replace(".wav", ".npz"),
        output_file=output_file,
        output_full=False,
        text_temp=text_temp,
        waveform_temp=waveform_temp,
    )
    return new_audio


def step_4_save_actor(
    actor_name,
    actor_bio,
    actor_physical_description,
    actor_catch_phrase,
    voice,
    voice_variation,
):
    """Save the actor as yaml, and save the voice variation as npz"""

    # save the voice variation as npz by copying the voice variation
    # to the speaker directory
    safe_actor_name = actor_name.replace(" ", "_").lower()
    speaker_file = os.path.join(utils.SPEAKER_PATH, (safe_actor_name + ".npz"))
    copy2(voice_variation.replace(".wav", ".npz"), speaker_file)
    # extract text_temp and waveform_temp from the filename
    text_temp, waveform_temp = voice_variation.replace(".wav", "").split("-")[-2:]
    text_temp = float(text_temp)
    waveform_temp = float(waveform_temp)

    # save the actor to yaml
    actor_dict = {
        "name": actor_name,
        "speaker": safe_actor_name + ".npz",
        "speaker_waveform_temp": waveform_temp,
        "speaker_text_temp": text_temp,
        "bio": actor_bio,
        "physical_description": actor_physical_description,
        "catch_phrase": actor_catch_phrase,
    }
    new_path = os.path.join(utils.ACTOR_PATH, f"{safe_actor_name}.yaml")
    with open(new_path, "w") as f:
        yaml.dump(actor_dict, f)

    return gr.Button.update(value=f"Saved {actor_name} to {new_path}")


def change_selected_voice(selected_voice):
    """Change the selected voice"""
    return selected_voice


def change_selected_variation(selected_variation):
    """Change the selected variation"""
    return selected_variation


def actor_creator_ui():
    with gr.Blocks("Actor Creator") as demo:
        actor_name = gr.inputs.Textbox(lines=1, label="Actor Name")
        with gr.Row():
            actor_bio = gr.inputs.Textbox(lines=5, label="Actor Bio")
            actor_physical_description = gr.inputs.Textbox(
                lines=5, label="Actor Physical Description"
            )
            with gr.Column():
                generate_bio_btn = gr.Button(value="Generate Bio")
        with gr.Row():
            gr.Markdown(
                """## Actor Voice Creation
            * Choose an initial sentence to start the voice creation
            * Click the button to generate 20 voices
            * The dropdown will show the generated voices
            * Choose a voice from the dropdown
            * Listen to the voice
            * If you like the voice, click the button to start step 2, and generate variations of temp and waveform
            """
            )
        with gr.Row():
            with gr.Column():
                initial_sentence = gr.inputs.Textbox(lines=1, label="Initial Sentence")
                num_samples_to_generate = gr.inputs.Slider(
                    minimum=1,
                    maximum=20,
                    step=1,
                    default=20,
                    label="Number of Samples to Generate",
                )
                text_temp = gr.inputs.Slider(
                    minimum=0.0,
                    maximum=1.0,
                    step=0.01,
                    default=0.8,
                    label="Text Temperature",
                )
                waveform_temp = gr.inputs.Slider(
                    minimum=0.0,
                    maximum=1.0,
                    step=0.01,
                    default=0.8,
                    label="Waveform Temperature",
                )
                generate_voice_btn = gr.Button(value="Step 1: Generate Voice")
            with gr.Column():
                list_of_voices = gr.Dropdown(label="List of Voices", interactive=True)
                voice = gr.Audio(label="Voice", type="filepath")
                generate_voice_variations_btn = gr.Button(
                    value="Step 2: Generate Voice Variations"
                )
            with gr.Column():
                list_of_voice_variations = gr.Dropdown(
                    label="List of Voice Variations", interactive=True
                )
                voice_variation = gr.Audio(label="Voice Variation", type="filepath")
                test_sentence = gr.inputs.Textbox(lines=1, label="Test Sentence")
                generate_test_from_variation_btn = gr.Button(
                    value="Step 3: Generate Test From Variation"
                )
        with gr.Row():
            gr.Markdown(
                """## Save Actor
            * If you like the voice, click the button to save the actor
            """
            )
            save_actor_btn = gr.Button(value="Save Actor")

            generate_bio_btn.click(
                fn=generate_bio,
                inputs=[actor_name, actor_bio],
                outputs=[actor_bio, actor_physical_description, initial_sentence],
            )
            generate_voice_btn.click(
                fn=step_1_generate_voices,
                inputs=[
                    initial_sentence,
                    num_samples_to_generate,
                    text_temp,
                    waveform_temp,
                ],
                outputs=list_of_voices,
            )
            list_of_voices.change(
                change_selected_voice, inputs=list_of_voices, outputs=voice
            )
            generate_voice_variations_btn.click(
                fn=step_2_generate_voice_variations,
                inputs=[initial_sentence, list_of_voices, text_temp, waveform_temp],
                outputs=list_of_voice_variations,
            )
            list_of_voice_variations.change(
                change_selected_variation,
                inputs=list_of_voice_variations,
                outputs=voice_variation,
            )
            generate_test_from_variation_btn.click(
                fn=step_3_generate_test_from_voice_variation,
                inputs=[test_sentence, list_of_voices, list_of_voice_variations],
                outputs=voice_variation,
            )

            save_actor_btn.click(
                fn=step_4_save_actor,
                inputs=[
                    actor_name,
                    actor_bio,
                    actor_physical_description,
                    initial_sentence,
                    list_of_voices,
                    list_of_voice_variations,
                ],
                outputs=[save_actor_btn],
            )

    return demo
