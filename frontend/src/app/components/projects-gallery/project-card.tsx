/** React component card to show Project preview  */
"use client";
import React from "react";
import Link from "next/link";
import {AICPProject} from "@/typings";

import { Card, CardHeader, CardBody, CardFooter } from "@nextui-org/react";

type Props = {
    project: AICPProject
  };

export function ProjectCard({project}: Props) {
    return (
                <Link href={`/projects/${project.id}`}>
        <Card className="w-[400px] m-5 ">
            <CardHeader className="flex gap-3">
                <h4>{project.name}</h4>
            </CardHeader>
            <CardBody>
                <p>{project.description}</p>
            </CardBody>
        </Card>
        </Link>
)
}