from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)


def evaluate_binary(model, X_test, y_test):
    y_pred = model.predict(X_test)

    report = classification_report(
        y_test, y_pred, target_names=["Benign", "Malicious"], digits=4
    )

    cm = confusion_matrix(y_test, y_pred)

    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, y_pred, average="binary"
    )

    return {
        "classification_report": report,
        "confusion_matrix": cm,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }
