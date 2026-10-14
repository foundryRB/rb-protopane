import { BrowserRouter, Route, Routes } from 'react-router-dom';

import { AmbientField } from '@/views/AmbientField';
import { EditorPage } from '@/views/EditorPage';
import { ProjectListPage } from '@/views/ProjectListPage';

export default function App() {
    return (
        <BrowserRouter>
            <AmbientField />
            <Routes>
                <Route path="/" element={<ProjectListPage />} />
                <Route path="/p/:slug" element={<EditorPage />} />
            </Routes>
        </BrowserRouter>
    );
}
