"use client";
import { useProject } from "@/hooks";
import React from "react";

type Props = {
    projectId: string
};

export function ProjectView({projectId}: Props) {
    const { project, error, isLoading } = useProject(projectId);
    if (isLoading) {
        return <div>Loading...</div>;
    }
    if (error) {
        return <div>{error.message}</div>;
    }
    return (
        <div>
            <h1>{project.name}</h1> 
        </div>
    );
}
