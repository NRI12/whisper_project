
// utils.js
function formatTimestamp(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${String(minutes).padStart(2, '0')}:${String(remainingSeconds).padStart(2, '0')}`;
}

class VideoDashboard {
    constructor() {
        // Khởi tạo các elements
        this.videoList = document.querySelector('.video-list');
        this.searchInput = document.querySelector('.search-bar input');
        this.videoInput = document.getElementById('videoInput');
        this.uploadBtn = document.getElementById('uploadBtn');
        this.transcriptionText = document.getElementById('transcriptionText');
        this.videoPlayer = document.getElementById('videoPlayer');
        this.downloadBtn = document.getElementById('downloadTranscript');
        this.currentTranscript = null; // Để lưu transcript hiện tại
        this.downloadBtn.addEventListener('click', () => this.downloadTranscription());

        this.translateBtn = document.getElementById("translateBtn")
        this.youtubeUrlInput = document.getElementById('youtubeUrlInput');
        this.processYouTubeBtn = document.getElementById('processYouTubeBtn');
        this.languageSelect = document.getElementById('languageSelect');

        // State management
        this.token = localStorage.getItem('token');
        this.videos = [];
        
        // Khởi tạo event listeners và load videos
        this.initializeEventListeners();
        this.loadVideos();
    }

    initializeEventListeners() {
        // Xử lý upload video
        this.uploadBtn.addEventListener('click', () => this.handleVideoUpload());
        this.videoInput.addEventListener('change', () => this.validateVideoFile());
        
        // Xử lý tìm kiếm
        this.searchInput.addEventListener('input', (e) => this.handleSearch(e));
        
        // Xử lý click vào video item
        this.videoList.addEventListener('click', (e) => {
            // Xử lý delete button
            if (e.target.closest('.delete-video')) {
                e.preventDefault();
                const videoId = e.target.closest('.delete-video').dataset.videoId;
                this.handleDeleteVideo(videoId);
                return;
            }
    
            // Xử lý click vào video item (giữ nguyên code cũ)
            const videoItem = e.target.closest('.video-item');
            if (videoItem && !videoItem.classList.contains('processing')) {
                const videoId = Number(videoItem.dataset.videoId); // Chắc chắn nó là số
                const video = this.videos.find(v => v.id === videoId);
                
                if (!video) {
                    console.error("DEBUG: Không tìm thấy video với ID:", videoId);
                    return;
                }
                console.log("DEBUG: Video đã chọn:", video);
                this.selectVideo(video);
                
            }
        });
        // Xử lý tải video từ YouTube
        this.processYouTubeBtn.addEventListener('click', () => this.handleYouTubeProcessing());
        // Xử lý dịch văn bản khi nhấn Translate
        this.translateBtn.addEventListener('click', () => this.handleTranslation());
    }
    async handleTranslation() {
        const targetLang = this.languageSelect.value;
        if (!targetLang || !this.currentTranscript) return;
    
        try {
            this.translateBtn.disabled = true;
            this.translateBtn.innerHTML = `
                <span class="spinner-border spinner-border-sm me-1"></span>
                Translating...
            `;    
            // Tạo prompt cho Gemini    
            const transcriptionText = this.currentTranscript?.text || "";
            const prompt = `Translate the following text into ${targetLang}.  
            ONLY return the translated text, no explanation, no commentary, no additional analysis.  
            Do not include explanations, notes, comments, or formatting.  
            Return only the translated text, nothing else.  

            Text to translate:  
            ${transcriptionText}`;
                
            console.log("DEBUG: Prompt for translation:", prompt);
    
            const response = await fetch("http://localhost:8000/generate_gemini_content", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${this.token}`
                },
                body: JSON.stringify({
                    text: transcriptionText,
                    language: targetLang
                })
            });
    
            if (!response.ok) throw new Error('Translation failed');
    
            const result = await response.json();
        
            // Cập nhật cả UI và this.currentTranscript.text
            this.currentTranscript.text = result.translated_text;
            console.log("update success")
            this.transcriptionText.innerHTML = `
                <div class="card">
                    <div class="card-body">
                        <p class="mb-0">${this.currentTranscript.text}</p>
                    </div>
                </div>
            `;
    
        } catch (error) {
            console.error('Translation error:', error);
            this.showError('Failed to translate. Please try again.');
        } finally {
            this.translateBtn.disabled = false;
            this.translateBtn.innerHTML = `
                <i class="fas fa-language me-1"></i>Translate
            `;
        }
    }
    async handleYouTubeProcessing() {
        const videoUrl = this.youtubeUrlInput.value.trim();
        if (!videoUrl) {
            this.showError('Please enter a valid YouTube video URL.');
            return;
        }
        if (!this.token) {
            this.showError('Authentication token is missing. Please login.');
            return;
        }

        try {
            this.showProcessingModal();

            const response = await fetch("http://localhost:8000/transcribe_and_download", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${this.token}`
                },
                body: JSON.stringify({ url: videoUrl })
            });

            const result = await response.json();
            this.hideProcessingModal();

            if (!response.ok) {
                throw new Error(result.detail || "An error occurred while processing the video.");
            }

            this.loadVideos();  // Refresh danh sách video
        } catch (error) {
            this.hideProcessingModal();
            this.showError(error.message);
        }
    }

    showProcessingModal() {
        const processingModal = new bootstrap.Modal(document.getElementById("processingModal"));
        processingModal.show();
    }

    hideProcessingModal() {
        const processingModalEl = document.getElementById("processingModal");
        const modalInstance = bootstrap.Modal.getInstance(processingModalEl);
        if (modalInstance) {
            modalInstance.hide();
        }
    }
    validateVideoFile() {
        const file = this.videoInput.files[0];
        if (file) {
            const isValid = file.type.startsWith('video/');
            this.uploadBtn.disabled = !isValid;
            
            if (!isValid) {
                alert('Please select a valid video file.');
                this.videoInput.value = '';
            }
        }
    }

    async loadVideos() {
        try {
            const response = await fetch('/transcription_histories', {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });
            if (!response.ok) throw new Error('Failed to fetch videos');
            this.videos = await response.json();
            this.renderVideoList();
        } catch (error) {
            console.error('Error loading videos:', error);
            this.showError('Failed to load videos. Please try again later.');
        }
    }
    async handleDeleteVideo(videoId) {
        if (!confirm('Are you sure you want to delete this video?')) return;
    
        try {
            const response = await fetch(`/transcribe/history/${videoId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });
    
            if (!response.ok) throw new Error('Failed to delete video');
    
            // Clear video player if deleted video is currently playing
            if (this.videoPlayer.src.includes(`/video/${videoId}`)) {
                this.videoPlayer.src = '';
                this.transcriptionText.innerHTML = '';
            }
    
            await this.loadVideos();
    
        } catch (error) {
            console.error('Error deleting video:', error);
            this.showError('Failed to delete video. Please try again.');
        }
    }
    renderVideoList() {
        if (!this.videos || this.videos.length === 0) {
            this.videoList.innerHTML = `
                <div class="text-center p-4">
                    <i class="fas fa-film text-muted mb-3" style="font-size: 3rem;"></i>
                    <p class="text-muted mb-0">No videos available</p>
                    <small class="text-muted">Click "Add Video" to upload a new video</small>
                </div>`;
            return;
        }
    
        this.videoList.innerHTML = this.videos.map(video => `
            <div class="video-item ${video.processing ? 'processing' : ''}" data-video-id="${video.id}">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h6 class="mb-1">${video.video_name}</h6>
                        <small class="text-muted">
                            ${video.processing ? 
                                '<span class="badge bg-warning"><i class="fas fa-spinner fa-spin me-1"></i>Processing</span>' : 
                                `Duration: ${formatTimestamp(video.video_duration)}`}
                        </small>
                        ${!video.processing && video.text ? 
                            '<div class="mt-1"><small class="text-success"><i class="fas fa-check me-1"></i>Transcribed</small></div>' :
                            ''}
                    </div>
                    <div class="dropdown">
                        <button class="btn btn-link text-dark" type="button" data-bs-toggle="dropdown">
                            <i class="fas fa-ellipsis-v"></i>
                        </button>
                        <ul class="dropdown-menu">
                            <li>
                                <a class="dropdown-item text-danger delete-video" href="#" data-video-id="${video.id}">
                                    <i class="fas fa-trash me-2"></i>Delete
                                </a>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        `).join('');
    }

    async selectVideo(video) {
        this.currentTranscript = null
        try {
            const videoUrl = `/video/${video.id}`;
            //Sử dụng fetch để stream với authorization header
            const response = await fetch(videoUrl, {
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Range': 'bytes=0-' // Thêm range header
                }
            });
    
            if (!response.ok) throw new Error('Failed to load video');
            
            // Tạo blob URL từ response
            const videoBlob = await response.blob();
            const videoObjectUrl = URL.createObjectURL(new Blob([videoBlob], { type: 'video/mp4' }));
            // Cleanup old URL
            if (this.videoPlayer.src) {
                URL.revokeObjectURL(this.videoPlayer.src);
            }
            console.log("DEBUG: videoObjectUrl", videoObjectUrl);
            this.videoPlayer.src = videoObjectUrl;
            this.videoPlayer.load();    
                
            // Lấy và hiển thị transcription
            const transcriptResponse = await fetch(`/transcribe/history/${video.id}`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });
    
            if (!transcriptResponse.ok) throw new Error('Failed to fetch video transcription');
    
            const data = await transcriptResponse.json();
            this.updateTranscription(data);
    
            // Highlight video đang chọn
            this.videoList.querySelectorAll('.video-item').forEach(item => {
                item.classList.toggle('active', item.dataset.videoId === String(video.id));
            });
    
            // Cleanup old object URL to prevent memory leaks
            // URL.revokeObjectURL(this.videoPlayer.src);
    
        } catch (error) {
            console.error('Error loading video:', error);
            this.showError('Failed to load video. Please try again.');
        }
    }
    async handleTranslation() {
        const targetLang = this.languageSelect.value;
        if (!targetLang || !this.currentTranscript) return;
    
        try {
            this.translateBtn.disabled = true;
            this.translateBtn.innerHTML = `
                <span class="spinner-border spinner-border-sm me-1"></span>
                Translating...
            `;
            console.log("DEBUG: currentTranscript", JSON.stringify(this.currentTranscript, null, 2));

            // Tạo prompt cho Gemini    
            const transcriptionText = this.currentTranscript?.text || "";
            const prompt = `Translate this text to ${targetLang}: ${transcriptionText}`;
            
            console.log("DEBUG: Prompt for translation:", prompt);
            const response = await fetch("http://localhost:8000/generate_gemini_content", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${this.token}`
                },
                body: JSON.stringify({
                    text: prompt,
                    language: targetLang
                })
            });
    
            if (!response.ok) throw new Error('Translation failed');
    
            const result = await response.json();
            
            this.currentTranscript.text = result.translated_text
            // Cập nhật UI với bản dịch
            this.transcriptionText.innerHTML = `
                <div class="card">
                    <div class="card-body">
                        <p class="mb-0">${result.translated_text}</p>
                    </div>
                </div>
            `;
    
        } catch (error) {
            console.error('Translation error:', error);
            this.showError('Failed to translate. Please try again.');
            this.updateTranscription(this.currentTranscript);
        } finally {
            this.translateBtn.disabled = false;
            this.translateBtn.innerHTML = `
                <i class="fas fa-language me-1"></i>Translate
            `;
        }
    }
    downloadTranscription() {    
        if (!this.currentTranscript || !this.currentTranscript.text) {
            console.error("DEBUG: No transcription text available.");
            return;
        }
            // Tạo file text
        const blob = new Blob([this.currentTranscript.text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
    
        // Tạo link tạm thời để download
        const a = document.createElement('a');
        a.href = url;
        a.download = `transcription_${new Date().getTime()}.txt`; // Tên file với timestamp
        document.body.appendChild(a);
        a.click();
    
        // Cleanup
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    updateTranscription(data) {    
        if (this.currentTranscript && this.currentTranscript.text !== data.text) {
            console.warn("DEBUG: Skipping update, already translated!");
            return;
        }
        this.currentTranscript = data; // Lưu lại transcript
        if (!data.text || typeof data.text !== "string") {
            console.error("DEBUG: No text found in transcription", data);
            this.downloadBtn.disabled = true; // Vô hiệu hóa nếu không có text
            return;
        }
    
        // Hiển thị nội dung transcription
        this.transcriptionText.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <p class="mb-0">${data.text}</p>
                </div>
            </div>
        `;
    
        this.downloadBtn.disabled = false; // Bật nút Download khi có text
    }
    
    handleSearch(e) {
        const searchTerm = e.target.value.toLowerCase();
        const filteredVideos = this.videos.filter(video => 
            video.video_name.toLowerCase().includes(searchTerm)
        );
        this.renderVideoList(filteredVideos);
    }

    showError(message) {
        const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
        document.getElementById('errorMessage').textContent = message;
        errorModal.show();
    }

    async handleVideoUpload() {
        const file = this.videoInput.files[0];
        if (!file) return;
    
        // Đóng modal upload
        const uploadModal = bootstrap.Modal.getInstance(document.getElementById('addVideoModal'));
        uploadModal.hide();
    
        // Hiển thị modal xử lý
        const processingModal = new bootstrap.Modal(document.getElementById('processingModal'));
        processingModal.show();
    
        const formData = new FormData();
        formData.append('file', file);
    
        try {
            const response = await fetch('/transcribe', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`
                },
                body: formData
            });
    
            if (!response.ok) throw new Error('Upload failed');
    
            const result = await response.json();
            
            // Update transcription text
            if (result.text) {
                this.updateTranscription(result);
            }
    
            // Refresh video list
            await this.loadVideos();
            
            // Reset form và đóng modal processing
            this.videoInput.value = '';
            processingModal.hide();
    
        } catch (error) {
            console.error('Error uploading video:', error);
            this.showError('Failed to upload video. Please try again.');
            processingModal.hide();
        }
    }
}

// Initialize khi DOM loaded
document.addEventListener('DOMContentLoaded', () => new VideoDashboard());