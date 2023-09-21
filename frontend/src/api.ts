import { AICPProject } from "./typings";
import createClient from "openapi-fetch";
import { paths } from "@/openapi"

const client = createClient<paths>({ baseUrl: process.env.AICP_API_HOST })
export async function getProjects() {
    let response = (await client.GET("/api/projects", {}))
    if (response.error || !response.data ){
        console.error(response.error);
        throw new Error("Failed to fetch projects")
    }
    let projects: [AICPProject] = response.data; 
    return projects;
}

export async function authenticate(username: string, password: string) {
    let response = (await client.POST("/api/auth/sign-in", { body: { username, password } }))
    if (response.error || !response.data ){
        console.error(response.error);
        throw new Error("Failed to authenticate")
    }
    return response.data;
}