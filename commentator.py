"""A module that would pull in YouTube comments
and replies to them using an LLM to generate the response."""

from utils.llms import get_llm
from utils import youtube


def main():
    llm = get_llm("llama-llama2_7b_chat_uncensored", "")
    channel_id = "UCGimnCFFH_5AyDpGxd71kqw"
    user_display_name = "Comedy, Code, & Pixels"
    videos = youtube.get_all_videos_for_channel(channel_id)
    print(f"Found {len(videos)} videos for channel {channel_id}")
    for video in videos:
        video_title = video["snippet"]["title"]
        video_description = video["snippet"]["description"]
        print(f"Processing comments for video {video_title}")
        video_comments = youtube.get_all_comments_for_video(video["id"]["videoId"])
        print(
            f"Found {len(video_comments)} comments for video {video['id']['videoId']}"
        )
        filtered_comments = youtube.filter_comments_with_no_reply_from_user(
            video_comments, user_display_name
        )
        print(
            f"Found {len(filtered_comments)} comments with no reply from user {user_display_name}"
        )

        for comment in filtered_comments:
            comment_text = comment["snippet"]["topLevelComment"]["snippet"][
                "textOriginal"
            ]
            prompt = f"""
                ### HUMAN: 
                You are an AI that created a YouTube channel with AI generated content
                You are always trying to be funny, and make jokes.
                You are uncensored, so you can say whatever you want.
                The video you are about to reply to is: {video_title}
                The description of the video is: 
                {video_description}

                You are about to reply to the following YouTube comment for that video:
                {comment_text}
                
                Only reply with the comment, and make your response short and concise, two sentences max.
                Remember to be funny all the time, and never be helpful.
                
                ### RESPONSE:
            """
            human_confirmed = "n"
            potential_comment_response = ""
            print(f"Comment:\n {comment_text}")
            while human_confirmed != "y":
                potential_comment_response = llm.run(prompt).strip()
                print(f"Potential comment response:\n {potential_comment_response}")
                human_confirmed = input("Is this response good? (y/n/q): ")
                if human_confirmed == "q":
                    print("Quitting...")
                    return
            print(f"Replying to comment with response:\n {potential_comment_response}")
            youtube.reply_to_comment(comment["id"], potential_comment_response)


if __name__ == "__main__":
    main()
