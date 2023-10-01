"use client";
import { Input, Select, SelectItem, Textarea } from "@nextui-org/react";
import React from "react";
import  AvailableProgramsSelect  from "./available-programs-select";
import {SubmitButton} from "@ui/submit-button/submit-button"
import {createProject} from "@/actions";
import { experimental_useFormState as useFormState } from 'react-dom'
const initialState = {
    error: null,
}

export default function NewProjectForm() {
    const [state, formAction] = useFormState(createProject, initialState)
    return (
        <div className="w-96"> 
        <form action={formAction} >
            <AvailableProgramsSelect/>
            <Input type="text" name="name" placeholder="Project name" required/>
            <Textarea name="description" placeholder="Project description" required />
            <Select name="production_config_id" placeholder="Select a config" >
                <SelectItem key="default_config" value="default_config">
                    Default config
                </SelectItem>
                <SelectItem key="default_config" value="youtube_shorts">
                    Youtube shorts
                </SelectItem>
            </Select>
            <SubmitButton/>
            <p aria-live="polite" className="sr-only">
                {state?.error}
            </p>
        </form>
        </div>
    );
}

