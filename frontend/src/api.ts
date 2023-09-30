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
    return response.data
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

export async function createProject(name: string, description: string) {
    let body = { 
        body: {
            name,
            description
        }
    }
    let response = (await client.POST("/api/projects/", body))
    if (response.error || !response.data ){
        console.error(response.error);
        throw new Error("Failed to create project")
    }
    return response.data;
}

export async function getProject(id: string) {
    const session = await getServerSession(authOptions)
    let response = (await client.GET(`/api/projects/{project_id}`,
    {
        params: {
            path: {
                project_id: id
            }
        },
        headers: {
            Authorization: `Bearer ${session.access_token}`
        }
    }))
    if (response.error || !response.data ){
        console.error(response.error);
        throw new Error("Failed to fetch project")
    }
    return response.data;
}

export async function listPrograms() {
    const session = await getServerSession(authOptions)
    let response = (await client.GET(`/api/programs/`,
    {
        headers: {
            Authorization: `Bearer ${session.access_token}`
        }
    }))
    if (response.error || !response.data ){
        console.error(response.error);
        throw new Error("Failed to fetch programs")
    }
    return response.data;
}

