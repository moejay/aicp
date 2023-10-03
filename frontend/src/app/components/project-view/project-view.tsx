"use client";
import { useProject } from "@/hooks";
import React from "react";
import { BookOpen } from "@ui/svgs/book-open";
import { VideoCamera } from "@ui/svgs/video-camera";
import { PaperAirplane } from "@ui/svgs/paper-airplane";
import Link from "next/link";

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
        <div >
            <div className="flex justify-center">
            <p className="text-5xl">{project.name}</p>
            </div>
        <div className="flex justify-evenly flex-row" >
                <Link href={`/projects/${project.id}/edit/script`}>
                <BookOpen/>
                </Link>
                <Link href={`/projects/${project.id}/edit/video`}>
                <VideoCamera />
                </Link>
                <Link href={`/projects/${project.id}/edit/export`}>
                <PaperAirplane />
                </Link>
        </div>
        </div>
    );
}
