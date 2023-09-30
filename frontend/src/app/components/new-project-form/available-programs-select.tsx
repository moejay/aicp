import { useAvailablePrograms } from "@/hooks";
import { Select, SelectItem } from "@nextui-org/react";
import React from "react";

export default function AvailableProgramsSelect() {
    const { programs, error, isLoading } = useAvailablePrograms();
    if (isLoading) {
        return <div>Loading...</div>;
    }
    return (
        <Select placeholder="Select a program" name="program_id" >
            {
                programs.map((program) => (
                    <SelectItem key={program.id} value={program.id}>
                        {program.title}
                    </SelectItem>
                ))
            }
        </Select>

    )
}