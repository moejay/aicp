"use client";
import { Input, Select, SelectItem, Textarea } from "@nextui-org/react";
import React from "react";
import  AvailableProgramsSelect  from "./available-programs-select";
import {SubmitButton} from "@ui/submit-button/submit-button"
import {createProject} from "@/actions";
export default function NewProjectForm() {
    return (
        <div className="w-96"> 
        <form action={createProject} >
            <AvailableProgramsSelect/>
            <Input type="text" name="name" placeholder="Project name" />
            <Textarea name="description" placeholder="Project description" />
            <Select name="production_config_id" placeholder="Select a config" >
                <SelectItem key="default_config" value="default_config">
                    Default config
                </SelectItem>
                <SelectItem key="default_config" value="youtube_shorts">
                    Youtube shorts
                </SelectItem>
            </Select>
            <SubmitButton/>
        </form>
        </div>
    );
}

