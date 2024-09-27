
async function transcribe(api, data) {
    try {
        const response = await fetch(api, {
            method: "POST",
            body: data
        });

        if (response.ok) {
            const data = await response.json();
            const taskId = data.task_id;

            // 創建進度條
            const progressBar = document.createElement('div');
            progressBar.className = 'progress-bar';
            progressBar.innerHTML = `
                <div class="progress-inner"></div>
                <div class="progress-text"></div>
            `;
            document.getElementById('result').innerText = '';
            document.getElementById('result').appendChild(progressBar);

            // 設定定時器檢查任務狀態
            const checkStatus = setInterval(async () => {
                const statusResponse = await fetch(`/api/task/${taskId}`);
                const statusData = await statusResponse.json();

                const progressInner = progressBar.querySelector('.progress-inner');
                const progressText = progressBar.querySelector('.progress-text');

                switch (statusData.task_status) {
                    case 'PENDING':
                        progressText.textContent = statusData.task_progress.message;
                        break;
                    case 'PROGRESS':
                        const progress = statusData.task_progress.current;
                        progressInner.style.width = `${progress}%`;
                        progressText.textContent = `${statusData.task_progress.message} ${progress}%`;
                        break;
                    case 'SUCCESS':
                        clearInterval(checkStatus);
                        progressBar.remove();
                        document.getElementById('result').innerHTML = `
                            <h2 style="text-align: center;">轉錄結果：</h2>
                            <p><strong>轉錄：</strong> ${statusData.task_result.transcription}</p>
                            <div id="summary">${statusData.task_result.summary}</div>
                        `;
                        break;
                    case 'FAILURE':
                        clearInterval(checkStatus);
                        progressBar.remove();
                        document.getElementById('result').textContent = '轉錄失敗，請稍後再試。';
                        break;
                }
            }, 1000);
        } else {
            throw new Error('檔案處理失敗');
        }
    } catch (error) {
        console.error("錯誤：", error);
        document.getElementById('result').textContent = "發生錯誤，請稍後再試。";
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}
