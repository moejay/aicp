import { AICPProject } from "./typings";
import createClient from "openapi-fetch";
import { paths } from "@/openapi"

const client = createClient<paths>({ baseUrl: process.env.AICP_API_HOST })
export async function getProjects() {
    console.log("Fetching projects")
    console.log("Client: ", client)
    let response = (await client.GET("/api/projects", {}))
    console.log(response);
    if (response.error || !response.data ){
        console.error(response.error);
        throw new Error("Failed to fetch projects")
    }
    let projects: [AICPProject] = response.data; 
    return projects;
}