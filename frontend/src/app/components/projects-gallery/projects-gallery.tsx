/* Projects list component */
import React from "react";
import { getProjects } from "@/api";
import { ProjectCard } from "./project-card";

export async function ProjectsGallery() {
    let projects = await getProjects();
    return (<div>
        <div className="flex" >
            {projects.map((project) => (
                <ProjectCard project={project}/>
            ))}
        </div>
    </div>
    )
}
