import { AICPProject } from "./typings";
import createClient from "openapi-fetch";
import { paths } from "@/openapi"
import { getServerSession } from "next-auth/next";
import {authOptions} from "@/app/api/auth/[...nextauth]/route"

const client = createClient<paths>({ baseUrl: process.env.AICP_API_HOST, headers: { "Content-Type": "application/json" } })
export async function getProjects() {
    const session = await getServerSession(authOptions)
    console.log(session)
    let response = (await client.GET("/api/projects/", {
        headers: {
            Authorization: `Bearer ${session.access_token}`
        }
    }))
    if (response.error || !response.data ){
        console.error(response.error);
        throw new Error("Failed to fetch projects")
    }
    let projects: [AICPProject] = response.data; 
    return projects;
}

export async function authenticate(username: string, password: string) {
    let response = (await client.POST("/api/users/sign-in", { body: { username, password } }))
    if (response.error || !response.data ){
        console.error(response.error);
        throw new Error("Failed to authenticate")
    }
    return response.data;
}

export async function refresh(refreshToken: string) {
    let response = (await client.POST("/api/users/refresh", { body: { refresh_token: refreshToken } }))
    if (response.error || !response.data ){
        console.error(response.error);
        throw new Error("Failed to refresh")
    }
    return response.data;
}
