"use client";
import { Input, Select, SelectItem, Textarea } from "@nextui-org/react";
import React from "react";
import  AvailableProgramsSelect  from "./available-programs-select";

export default function NewProjectForm() {
    return (
        <div className="w-96"> 
            <AvailableProgramsSelect/>
            <Input type="text" placeholder="Project name" />
            <Textarea placeholder="Project description" />
            <Select placeholder="Select a config" >
                <SelectItem key="1" value="default_config">
                    Default config
                </SelectItem>
                <SelectItem key="2" value="youtube_shorts">
                    Youtube shorts
                </SelectItem>
            </Select>
        </div>
    );
}

