#!/usr/bin/env bash

APIKEY=$(yq .apikey ~/.runpod.yaml)
ENDPOINT=https://api.runpod.ai/v2/58ynxwpvuupl28/runsync

curl -X POST -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${APIKEY}" \
    -d '{"input":{"prompt":"bust of jack skellington, silhouette of haunted town, silhouette of bats in sky, vector logo style, flat design, high contrast, greyscale, circular","negative_prompt":"background, texture, text, extra legs, extra limbs, extra arms, extra fingers","width":768,"height":768,"num_outputs":5,"num_inference_steps":30,"scheduler":"DDIM"}}' \
    ${ENDPOINT} > output.json

DATE=$(date '+%s')
mkdir -p images/$DATE
i=1
for image in $(cat output.json | jq -r '.output[].image'); do
    echo $image | base64 -d > images/${DATE}/image${i}.png
    i=$((i+1));
done
