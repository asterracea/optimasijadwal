document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById("modalDeleteGen");
    const deleteForm = document.getElementById("form-delete");

    document.querySelectorAll("button[data-id]").forEach(button => {
      button.addEventListener("click", function () {
        const id = this.getAttribute("data-id");
        deleteForm.action = `/data/generate/delete/${id}`;
        modal.classList.remove("hidden");
      });
    });
  });

  function closeModal() {
    document.getElementById("modalDeleteGen").classList.add("hidden");
  }
