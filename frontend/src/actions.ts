'use server'
import * as api from '@/api'
import { redirect } from "next/navigation"
import { AICPProjectCreate } from '@/typings'
export async function createProject(prevState: any, formData: FormData) {
    try {
        let projectCreate: AICPProjectCreate = {
            name: formData.get('name') as string,
            description: formData.get('description') as string,
            program_id: formData.get('program_id') as string,
            production_config_id: formData.get('production_config_id') as string,
        }
        let response = await api.createProject(projectCreate)
        redirect(`/projects/${response.id}`)

        } catch (error) {
            console.error(error)
            return {
                "error": "Failed to create project"
            }
        }
}