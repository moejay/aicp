/* Card with a big plus button to create a new project */
"use client"
import React from "react";
import Link from "next/link";
import {PlusSign} from "@ui/svgs/plus-sign";

import { Card, CardHeader, CardBody, CardFooter } from "@nextui-org/react";

export function NewProjectCard() {
    return (
        <Card className="w-[400px] m-5 ">
            <CardHeader className="flex gap-3">
                <h4>New project</h4>
            </CardHeader>
            <CardBody>
                <PlusSign/>
            </CardBody>
            <CardFooter>
                <Link href={`/projects/new`}>
                    Create a new project
                </Link>
            </CardFooter>
        </Card>
    )
}