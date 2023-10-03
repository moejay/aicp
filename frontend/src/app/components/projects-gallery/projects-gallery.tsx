"use client";
/* Projects list component */
import React from "react";
import { ProjectCard } from "./project-card";
import { NewProjectCard } from "./new-project-card";
import { useProjects } from "@/hooks";

export function ProjectsGallery() {
    const { projects, error, isLoading } = useProjects();
    if (isLoading) {
        return <div>Loading...</div>;
    }
    if (error) {
        return <div>{error.message}</div>;
    }
    return (<div className="flex w-full justify-center ">
        <div className="max-w-[1300px] grid grid-cols-3 grid-flow-row-dense" >
            <NewProjectCard/>
            {projects.map((project) => (
                <ProjectCard project={project}/>
            ))}
        </div>
    </div>
    )
}
