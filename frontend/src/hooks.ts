import useSWR from 'swr';

const fetcher = (...args) => fetch(...args).then(res => res.json())

export function useUser() {
    const { data, error } = useSWR('/api/users/me', fetcher)
    return {
        user: data,
        isLoading: !error && !data,
        isError: error
    }
}

export function useProjects() {
    const { data, error } = useSWR('/api/projects/', fetcher)
    return {
        projects: data,
        isLoading: !error && !data,
        isError: error
    }
}

export function useProject(id: string) {
    const { data, error } = useSWR(`/api/projects/${id}`, fetcher)
    return {
        project: data,
        isLoading: !error && !data,
        isError: error
    }
}

export function useAvailablePrograms() {
    const { data, error } = useSWR('/api/programs/', fetcher)
    return {
        programs: data,
        isLoading: !error && !data,
        isError: error
    }
}