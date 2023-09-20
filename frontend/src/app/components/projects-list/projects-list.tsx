/* Projects list component */
import React from "react";
import { AICPProject } from "@/typings";
import Link from "next/link";

export async function ProjectsList() {
    let projects: [AICPProject] = await (await fetch('http://backend:80/api/projects', { cache: 'no-store' })).json();
    return (<div>
        <div className="text-gray-900" >
            <h2 className="flex text-gray-900">Projects</h2>
            <ul>
            {projects.map((project) => (
                <li key={project.id}>
                <Link className="text-gray-900" href={`/projects/${project.id}`}>
                    {project.name}
                </Link>
                </li>
            ))}
            </ul>
        </div>
    </div>
    )
}
